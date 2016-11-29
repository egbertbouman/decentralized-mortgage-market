import time

from market.api.crypto import generate_key, get_public_key
from market.database.database import Database
from market.models.user import User
from market.models.profiles import Profile
from market.models.profiles import BorrowersProfile


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
        user = User(new_keys[0], time.time())  # Save the public key bin (encode as HEX) in the database along with the register time.

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

    def create_profile(self, user):
        """
        Create a new empty profile and save it to the database.
        :param user: the public key of the user
        :return:a Profile-object if the user is an investor, a BorrowersProfile-object if the user is a borrower, None else.
        """
        user_role = self.db.get('role', user.id)

        if user_role.role == 'INVESTOR':
            new_profile = Profile(user.id, "", "", "", "", "")
            self.db.post('profile', new_profile)
            return new_profile
        elif user_role.role == 'BORROWER':
            new_profile = BorrowersProfile(user.id, "", "", "", "", "", "", "", "")
            self.db.post('borrowers_profile', new_profile)
            return new_profile
        else:
            return None

    def load_profile(self, user):
        pass

    def place_loan_offer(self):
        """ post the data needed for placing a loan offer """
        pass

    def resell_investment(self):
        """ post the data needed to resell the investment """
        pass

    def load_investments(self):
        """ get the data from current and pending investments """
        pass

    def load_open_market(self):
        """ get the 'to be displayed on the open market' data  """
        pass

    def browse_system(self):
        """ open a dialog window to browse the user's system (to upload their private key) """
        pass

    def remember_user(self):
        """ save the user's login credentials on their system """
        pass

    def generate_keys(self):
        """ generate a new key pair """
        pass

    def check_role(self):
        """ check which role the user has """
        pass

    def create_loan_request(self):
        """ create a new loan request """
        pass

    def load_borrowers_loans(self):
        """ display all of the borrower's current loans """
        pass

    def load_borrowers_offers(self):
        """ display all of the borrower's current offers """
        pass

    def accept_offer(self):
        """ accept an offer """
        pass

    def reject_offer(self):
        """ reject an offer """
        pass

    def load_all_loan_request(self, bank_id):
        """ load all pending loan requests for a specific bank """
        pass

    def load_single_loan_request(self, loan_request_id):
        """ load a specific loan request to """
        pass

    def accept_loan_request(self, loan_request_id):
        """ accept a pending loan request """
        pass

    def reject_loan_request(self, loan_request_id):
        """ reject a pending loan request """
        pass
