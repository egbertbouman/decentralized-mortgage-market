import time
from datetime import timedelta
from market.api.crypto import generate_key, get_public_key
from market.database.database import Database
from market.models.house import House
from market.models.loans import LoanRequest, Mortgage, Investment, Campaign
from market.models.profiles import BorrowersProfile
from market.models.profiles import Profile
from market.models.role import Role
from market.models.user import User

STATUS = (
    'NONE',
    'PENDING',
    'ACCEPTED',
    'REJECTED'
)

class MarketAPI(object):
    def __init__(self, database):
        assert isinstance(database, Database)
        self._database = database
        self._user_key = None

    @property
    def db(self):
        return self._database

    @property
    def user_key(self):
        return self._user_key

    def create_user(self):
        """
        Create a new user and saves it to the database.
        :return: A tuple (User, public_key, private_key) or None if saving failed.
        """
        new_keys = generate_key()
        user = User(public_key=new_keys[0], time_added=time.time())  # Save the public key bin (encode as HEX) in the database along with the register time.

        if self.db.post(user.type, user):
            return user, new_keys[0], new_keys[1]
        else:
            return None

    def login_user(self, private_key):
        """
        Login a user by generating the public key from the private key and grabbing the user object using the generated key.
        :param public_key:
        :param private_key:
        :return:
        """
        if get_public_key(private_key):
            user = self.db.get('users', get_public_key(private_key))

            return user
        return None

    def create_profile(self, user, payload):
        """
        Creates a new profile and saves it to the database.
        :param user:
        :param payload:
        :return:
        """
        assert isinstance(user, User)
        assert isinstance(payload, dict)

        try:
            role = Role(user.id, payload['role'])
            user.role_id = self.db.post(role.type, role)

            profile = None
            if role.role_name == 'INVESTOR':
                profile = Profile(payload['first_name'], payload['last_name'], payload['email'], payload['iban'], payload['phonenumber'])
            elif role.role_name == 'BORROWER':
                profile = BorrowersProfile(payload['first_name'], payload['last_name'], payload['email'], payload['iban'],
                                           payload['phonenumber'], payload['current_postalcode'], payload['current_housenumber'], payload['documents_list'])
            else:
                return False

            user.profile_id = self.db.post(profile.type, profile)
            self.db.put(user.type, user.id, user)
            return profile
        except KeyError:
            return False

    def load_profile(self, user):
        """
        Get the profile from the database.
        :param user:
        :return:
        """
        role = self.db.get('role', user.role_id)

        profile = None
        if role.role_name == 'INVESTOR':
            profile = self.db.get('profile', user.profile_id)
        elif role.role_name == 'BORROWER':
            profile = self.db.get('borrowers_profile', user.profile_id)
        else:
            return False

        return profile

    # TODO: fix this function: mortgage is None-type somehow
    def place_loan_offer(self, user, payload):
        """
        Create a loan offer and save it to the database.
        :param user: User-object, in this case the user has the role of a borrower
        :param payload:
        :return:
        """
        assert isinstance(user, User)
        assert isinstance(payload, dict)

        role = self.db.get('role', user.role_id)

        if role.role_name == 'INVESTOR':
            loan_offer = Investment(payload['user_key'], payload['amount'], payload['duration'], payload['interest_rate'],
                                    payload['mortgage_id'], payload['status'])

            # Update the investor
            investment_id = self.db.post('investment', loan_offer)
            user.investment_ids.append(investment_id)
            self.db.put('users', user.id, user)

            # Update the borrower
            mortgage = self.db.get('mortgage', loan_offer.mortgage_id)
            loan_request = self.db.get('loan_request', mortgage.request_id)
            borrower = self.db.get('users', loan_request.user_key)
            borrower.investment_ids.append(loan_offer.id)
            self.db.put('users', borrower.id, borrower)

            return loan_offer
        else:
            return False

    def resell_investment(self):
        """ post the data needed to resell the investment """
        pass

    def load_investments(self, user):
        """
        Get the current investments list and the pending investments list from the database.
        :param user:
        :return:
        """
        current_investments = []
        pending_investments = []
        for investment_id in user.investment_ids:
            if self.db.get('investment', investment_id).status == "ACCEPTED":
                current_investments.append(self.db.get('investment', investment_id))
            elif self.db.get('investment', investment_id).status == "PENDING":
                pending_investments.append(self.db.get('investment', investment_id))
            else:
                pass
        return current_investments, pending_investments

    def load_open_market(self):
        """ get all open campaigns  """

        pass

    def check_role(self, user):
        """
        Get the role of the user from the database.
        :param user:
        :return:
        """
        return self.db.get('role', user.role_id)

    def create_loan_request(self, user, payload):
        """ Create a new loan request """
        assert isinstance(user, User)
        assert isinstance(payload, dict)

        role = self.db.get('role', user.role_id)

        # Only create a loan request if the user is a borrower
        loan_request = []
        if role.role_name == 'BORROWER':
            if not user.loan_request_ids:
                # Create the house
                house = House(payload['postal_code'], payload['house_number'], payload['price'])
                house_id = str(self.db.post('house', house))
                payload['house_id'] = house_id

                # Set status of the loan request to pending
                payload['status'] = payload['status'].fromkeys(payload['banks'], STATUS[1])

                loan_request = LoanRequest(user.id, house_id, payload['mortgage_type'], payload['banks'], payload['description'], payload['amount_wanted'], payload['status'])

                # Add the loan request to the borrower
                user.loan_request_ids.append(self.db.post('loan_request', loan_request))
                self.db.put('users', user.id, user)

                # Add the loan request to the banks' pending loan request list
                for bank_id in payload['banks']:
                    bank = self.db.get('users', bank_id)
                    assert isinstance(bank, User)
                    bank.loan_request_ids.append(user.loan_request_ids[0])
                    self.db.put('users', bank.id, bank)

                return loan_request

            else:
                return False
        else:
            return False

    # TODO: write test for this function after the accept_offer has been implemented
    def load_borrowers_loans(self, user):
        """
        Get the borrower's current active loans (funding goal has been reached) or the not yet active loans (funding goal has not been reached yet)
        :param user: User-object, in this case the user has the role of a borrower
        :return: list of the loans, containing either the current active loans or the not yet active loans
        """
        loans = []
        for mortgage_id in user.mortgage_ids:
            if self.db.get('mortgage', mortgage_id).status == "ACCEPTED":
                mortgage = self.db.get('mortgage', mortgage_id)
                # Add the accepted mortgage in the loans list
                loans.append(mortgage)
                campaign = self.db.get('campaign', user.campaign_ids[0])
                for investor_id in mortgage.investors:
                    investor = self.db.get('users', investor_id)
                    for investment_id in investor.investment_ids:
                        investment = self.db.get('investment', investment_id)
                        # Add the loan to the loans list if the mortgage id's match and the funding goal has been reached
                        if investment.mortgage_id == mortgage_id and campaign.status == True:
                            loans.append(investment)
                        # Add the loan to the loans list if the mortgage id's match and the funding goal has not been reached
                        elif investment.mortgage_id == mortgage_id and campaign.status == False:
                            loans.append(investment)

        return loans

    def load_borrowers_offers(self, user):
        """
        Get all the borrower's offers(mortgage offers or loan offers) from the database.
        :param user: User-object, in this case the user has the role of a borrower
        :return: list of offers, containing either mortgage offers or investment offers
        """
        # Reload the user to get the latest data from the database.
        user = self.db.get(user.type, user.id)
        offers = []
        for mortgage_id in user.mortgage_ids:
            # If the mortgage is already accepted, we get the loan offers from the investors
            if self.db.get('mortgage', mortgage_id).status == "ACCEPTED":
                mortgage = self.db.get('mortgage', mortgage_id)
                print "mort stat ", mortgage.status

                for investor_id in mortgage.investors:
                    investor = self.db.get('users', investor_id)
                    for investment_id in investor.investment_ids:
                        if self.db.get('investment', investment_id).status == "PENDING":
                            investment_offer = self.db.get('investment', investment_id)
                            offers.append(investment_offer)

                return offers
            # If the mortgage has not yet been accepted, get the mortgage offers from the banks
            elif self.db.get('mortgage', mortgage_id).status == "PENDING":
                mortgage = self.db.get('mortgage', mortgage_id)
                offers.append(mortgage)

        return offers

    # TODO: write tests
    def accept_offer(self, user, payload):
        """
        Accept a mortgage offer if the loan request has not been accepted yet or accept an investment offer if the user
        has already accepted a mortgage offer.
        :param user:
        :param payload:
        :return:
        """
        loan_request = self.db.get('loan_request', user.loan_request_id)
        banks = loan_request.status

        for bank in banks:
            # If the loan request has been accepted, only investment offers can be accepted
            if bank['status'] == "ACCEPTED":
                for mortgage in user.mortgage_ids:
                    # Only when the mortgage has been accepted, can the borrower accept investment offers
                    if mortgage.status == "ACCEPTED":
                        current_mortgage = self.db.get('mortgage', mortgage.id)
                        for investment in user.investment_ids:
                            investment_offer = self.db.get('investment', investment.id)
                            investor = self.db.get('users', investment_offer.user_key)
                            if investment_offer.mortgage_id == mortgage.id and investor.user_key == payload['user_key'] \
                                    and investment_offer.status == "pending" and investment_offer.amount == payload['amount'] \
                                    and investment_offer.duration == payload['duration'] and investment_offer.interest_rate == payload['interest_rate']:
                                    # Update the investment
                                    investment_offer.status = "ACCEPTED"
                                    self.db.put('investment', investment_offer.id, investment_offer)
                                    # Update the investor
                                    self.db.put('users', investor.id, investor)
                                    # Update the campaign
                                    campaign = self.db.get('campaign', user.campaign_ids[0])
                                    new_amount = campaign.amount - investment_offer.amount
                                    campaign.amount = new_amount
                                    if new_amount == 0:
                                        campaign.amount = 0
                                        campaign.completed = True
                                    self.db.put('campaign', campaign.id, campaign)
                                    # Update the user (borrower)
                                    self.db.put('users', user.id, user)

                                    return investment_offer
            # If the loan request has not been accepted yet, only mortgage offers can be accepted
            elif bank['status'] == "PENDING":
                for mortgage in user.mortgage_ids:
                    if mortgage.request_id == payload['request_id'] and mortgage.house_id == payload['house_id'] and mortgage.bank == payload['bank'] \
                        and mortgage.amount == payload['amount'] and mortgage.mortgage_type == payload['mortgage_type'] \
                        and mortgage.interest_rate == payload['interest_rate'] and mortgage.max_invest_rate == payload['max_invest_rate'] \
                        and mortgage.default_rate == payload['default_rate'] and mortgage.default_rate == payload['duration'] \
                        and mortgage.risk == payload['risk'] and mortgage.investors == payload['investors'] and mortgage.status == payload['status']:
                        current_bank = self.db.get('users', payload['bank'])
                        # Update the mortgage
                        mortgage.status = "ACCEPTED"
                        self.db.put('mortgage', mortgage.id, mortgage)
                        bank['status'] = "ACCEPTED"
                        # Set the status of other mortgage offers to 'REJECTED'
                        for bank_others in banks:
                            if bank_others['status'] == "PENDING":
                                bank_others['status'] = "REJECTED:"
                        # Update loan request in the database
                        loan_request.db.put('loan_request', loan_request.id, loan_request)
                        # Add the newly created campaign to the database
                        end_date = time.strftime("%d/%m/%Y") + timedelta(days=30)
                        campaign = Campaign(mortgage.id, loan_request.amount_wanted, end_date, "accepted")
                        user.campaign_ids.append(campaign.id)
                        current_bank.campaign_ids.append(campaign.id)
                        self.db.post('campaign', campaign)
                        # Update the borrower
                        self.db.put('users', user.id, user)
                        # Update the bank
                        self.db.put('users', current_bank.id, current_bank)

                        return self.db.get('mortgage', mortgage)

        return False

    def reject_offer(self, user, payload):
        """ reject an offer """
        # TODO offer can be mortgage or investment
        pass

    def load_all_loan_requests(self, user):
        """ load all pending loan requests for a specific bank """
        assert isinstance(user, User)

        role = self.db.get('role', user.role_id)
        assert isinstance(role, Role)

        if role.role_name == 'FINANCIAL_INSTITUTION':
            pending_loan_requests = []

            # Only show loan requests that are still pending
            for pending_loan_request_id in user.loan_request_ids:
                if self.db.get('loan_request', pending_loan_request_id).status[user.id] == STATUS[1]:
                    pending_loan_requests.append(pending_loan_request_id)

            return pending_loan_requests
        else:
            return False

    def load_single_loan_request(self, payload):
        """ load a specific loan request """
        assert isinstance(payload, dict)

        loan_request = self.db.get('loan_request', payload['loan_request_id'])
        assert isinstance(loan_request, LoanRequest)

        return loan_request

    def accept_loan_request(self, user, payload):
        """ accept a pending loan request """
        assert isinstance(user, User)
        assert isinstance(payload, dict)

        # Accept the loan request
        accepted_loan_request = self.db.get('loan_request', payload['request_id'])
        assert isinstance(accepted_loan_request, LoanRequest)
        accepted_loan_request.status[user.id] = STATUS[2]

        # Create a mortgage
        mortgage = Mortgage(accepted_loan_request.id, payload['house_id'], user.id, payload['amount'], payload['mortgage_type'], payload['interest_rate'], payload['max_invest_rate'], payload['default_rate'], payload['duration'], payload['risk'], payload['investors'], STATUS[1])
        borrower = self.db.get('users', payload['user_key'])
        assert isinstance(borrower, User)

        # Add mortgage to borrower
        mortgage_id = self.db.post('mortgage', mortgage)
        borrower.mortgage_ids.append(mortgage_id)
        self.db.put(borrower.type, borrower.id, borrower)

        # Add mortgage to bank
        user.mortgage_ids.append(mortgage_id)
        self.db.put('users', user.id, user)

        # Save the accepted loan request
        if self.db.put('loan_request', accepted_loan_request.id, accepted_loan_request):
            return accepted_loan_request, mortgage
        else:
            return None

    def reject_loan_request(self, user, payload):
        """ reject a pending loan request """
        assert isinstance(user, User)
        assert isinstance(payload, dict)

        # Reject the loan request
        rejected_loan_request = self.db.get('loan_request', payload['request_id'])
        assert isinstance(rejected_loan_request, LoanRequest)
        rejected_loan_request.status[user.id] = STATUS[3]

        # Save rejected loan request
        borrower = self.db.get('users', payload['user_key'])
        assert isinstance(borrower, User)
        loan_request_id = borrower.loan_request_ids[0]

        # Check if the loan request has been rejected by all selected banks
        rejected = True
        for bank in rejected_loan_request.status:
            if rejected_loan_request.status[bank] != STATUS[3]:
                rejected = False

        # If all banks have rejected the loan request, remove the loan request from borrower
        if rejected:
            del borrower.loan_request_ids[:]
            self.db.put(borrower.type, borrower.id, borrower)

        # Save the rejected loan request
        if self.db.put('loan_request', loan_request_id, rejected_loan_request):
            return rejected_loan_request
        else:
            return None
