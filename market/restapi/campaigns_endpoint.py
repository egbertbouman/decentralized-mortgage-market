import json

from twisted.web import http
from twisted.web import resource

from market.models.investment import InvestmentStatus
from market.restapi import split_composite_key


class CampaignsEndpoint(resource.Resource):
    """
    This class handles requests regarding campaigns in the mortgage market community.
    """

    def __init__(self, community):
        resource.Resource.__init__(self)
        self.community = community

    def render_GET(self, request):
        """
        .. http:get:: /campaigns

        A GET request to this endpoint returns information about the ongoing campaigns.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/campaigns

            **Example response**:

            .. sourcecode:: javascript

                {
                    "campaigns": [{
                        "id": 8593AB_23,
                        "mortgage": {
                            "user_id": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
                            "house": {
                                "postal_code": "8593AB",
                                "house_number": "23",
                                "address": "Teststraat, Rotterdam",
                                "price": 395000,
                                "url": "http://www.funda.nl/koop/hollandscheveld/huis-49981036-3e-zandwijkje-8/",
                                "seller_phone_number": "+31685938573",
                                "seller_email": "seller@gmail.com"
                            },
                            "bank": "ABN",
                            "amount": 395000,
                            "bank_amount": 200000,
                            "mortgage_type": "FIXEDRATE",
                            "interest_rate": 5.3,
                            "max_investment_rate": 4.3,
                            "default_rate": 4.3,
                            "duration": 120,
                            "risk": 300000,
                            "status": "ACCEPTED"
                        },
                        "amount": "195000",
                        "end_time": "1489934141",
                        "completed": False
                    }, ...]
                }
        """
        return json.dumps({"campaigns": [campaign.to_dict(api_response=True)
                                         for campaign in self.community.data_manager.get_campaigns()]})

    def getChild(self, path, request):
        return SpecificCampaignEndpoint(self.community, path)


class SpecificCampaignEndpoint(resource.Resource):
    """
    This class handles requests for a specific campaign.
    """

    def __init__(self, community, campaign_composite_key):
        resource.Resource.__init__(self)
        self.community = community
        self.campaign_composite_key = campaign_composite_key

        self.putChild("investments", CampaignInvestmentsEndpoint(community, campaign_composite_key))

    def render_GET(self, request):
        """
        .. http:get:: /campaigns/(string: campaign_id)

        A GET request to this endpoint returns detailled information about a specific campaign.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/campaigns/8593AB_89

            **Example response**:

            .. sourcecode:: javascript

                {
                    "campaign": {
                        "id": "8593AB_89",
                        "user_id": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
                        "mortgage": {
                            "user_id": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
                            "house": {
                                "postal_code": "8593AB",
                                "house_number": "23",
                                "address": "Teststraat, Rotterdam",
                                "price": 395000,
                                "url": "http://www.funda.nl/koop/hollandscheveld/huis-49981036-3e-zandwijkje-8/",
                                "seller_phone_number": "+31685938573",
                                "seller_email": "seller@gmail.com"
                            },
                            "bank": "ABN",
                            "amount": 395000,
                            "bank_amount": 200000,
                            "mortgage_type": "FIXEDRATE",
                            "interest_rate": 5.3,
                            "max_investment_rate": 4.3,
                            "default_rate": 4.3,
                            "duration": 120,
                            "risk": 300000,
                            "status": "ACCEPTED"
                        },
                        "amount": "195000",
                        "end_time": "1489934141",
                        "completed": False
                    }
                }
        """
        keys = split_composite_key(self.campaign_composite_key)
        campaign = self.community.data_manager.get_campaign(*keys) if keys is not None else None
        if not campaign:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "campaign not found"})

        return json.dumps({"campaign": campaign.to_dict(api_response=True)})


class CampaignInvestmentsEndpoint(resource.Resource):
    """
    This class handles requests regarding investments of a particular campaign
    """
    def __init__(self, community, campaign_composite_key):
        resource.Resource.__init__(self)
        self.community = community
        self.campaign_composite_key = campaign_composite_key

    def getChild(self, path, request):
        return SpecificCampaignInvestmentEndpoint(self.community, self.campaign_composite_key, path)

    def render_GET(self, request):
        """
        .. http:get:: /campaigns/(string: campaign_id)/investments

        A GET request to this endpoint returns a list of investments of a campaign.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/campaigns/8593AB_89/investments

            **Example response**:

            .. sourcecode:: javascript

                {
                    "investments": [{
                        "investor_id": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
                        "amount": 9000,
                        "duration": 24,
                        "interest_rate": 4.9,
                        "mortgage_id": "8593AB_89",
                        "status": "ACCEPTED"
                    }, ...]
                }
        """
        keys = split_composite_key(self.campaign_composite_key)
        campaign = self.community.data_manager.get_campaign(*keys) if keys is not None else None
        if not campaign:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "campaign not found"})

        return json.dumps({"investments": [investment.to_dict(api_response=True) for investment in campaign.investments]})


class SpecificCampaignInvestmentEndpoint(resource.Resource):
    """
    This class handles requests for a specific investment in a campaign
    """
    def __init__(self, community, campaign_composite_key, investment_composite_key):
        resource.Resource.__init__(self)
        self.community = community
        self.campaign_composite_key = campaign_composite_key
        self.investment_composite_key = investment_composite_key

    def render_PATCH(self, request):
        """
        .. http:patch:: /campaigns/(string: campaign_id)/investments/(string: investment_id)

        A PATCH request to this endpoint will accept/reject an investment offer. This is performed by the borrower
        of a mortgage.

            **Example request**:

                .. sourcecode:: none

                    curl -X PATCH http://localhost:8085/campaigns/8948EE_43/investments/4344503b7e797ebf31582327a5baae35b11bda01
                    --data "state=ACCEPT"

            **Example response**:

                .. sourcecode:: javascript

                    {"success": True}
        """
        keys = split_composite_key(self.campaign_composite_key)
        campaign = self.community.data_manager.get_campaign(*keys) if keys is not None else None
        if not campaign:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "campaign not found"})

        keys = split_composite_key(self.investment_composite_key)
        investment = self.community.data_manager.get_investment(*keys) if keys is not None else None
        if not investment or investment.campaign_id != campaign.id:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "investment not found"})

        parameters = json.loads(request.content.read())
        status = parameters.get('status')
        if not status:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "missing status parameter"})

        if status not in ['ACCEPT', 'REJECT']:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "invalid status value"})

        if investment.status != InvestmentStatus.PENDING:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "loan request is already accepted/rejected"})

        if status == "ACCEPT":
            investment.status = InvestmentStatus.ACCEPTED
            campaign.amount_invested += investment.amount
            self.community.accept_investment(investment)
        else:
            investment.status = InvestmentStatus.REJECTED
            self.community.reject_investment(investment)

        return json.dumps({"success": True})
