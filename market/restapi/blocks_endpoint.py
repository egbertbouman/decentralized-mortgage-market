import json

from twisted.web import resource, http
from base64 import urlsafe_b64decode


class BlocksEndpoint(resource.Resource):
    """
    This class handles requests regarding the blockchain in the mortgage market community.
    """

    def __init__(self, community):
        resource.Resource.__init__(self)
        self.community = community

    def render_GET(self, request):
        """
        .. http:get:: /blocks

        A GET request to this endpoint returns a list of block in the blockchain.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/blocks

            **Example response**:

            .. sourcecode:: javascript

                {
                    "blocks": [{
                        "creator": "TGliTmFDTFBLOrhXMbHGgk_Pq0TXYqMOCY7FTbtvwe3sXm9XbbzO0bkPsYfofTeAUUDtcBiPCEP2ntMQLdF-oeVr5FeXPoEbwpE=",
                        "contracts": [],
                        "merkle_root_hash": "pXaGVQhfwppLvJf1aeiDIbIjuNUZKDgAVetusHpwRLw=",
                        "creator_signature": "hDOKk_4lRsFh2eDr5-JL_j30rwUbWSq1DkvkxIxyS4jXNUd2somAY8gyByu6j7YcOp3XIoedXqvNCzUvA1c2Dw==",
                        "time": 1493046869,
                        "id": "ADxyGf6VmgZduESTrQCHDxEJjLX0WPmg9gXjq18j8nc=",
                        "previous_hash": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
                        "target_difficulty": "00ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
                    }, ...]
                }
        """

        limit = min(250, int(request.args['limit'][0])) if 'limit' in request.args else 250
        blocks = []
        for index in self.community.data_manager.get_block_indexes(limit):
            block = self.community.data_manager.get_block(index.block_id)
            if block:
                block_dict = block.to_dict(api_response=True)
                block_dict["height"] = index.height
                blocks.append(block_dict)

        return json.dumps({"blocks": blocks})

    def getChild(self, path, request):
        return SpecificBlockEndpoint(self.community, path)


class SpecificBlockEndpoint(resource.Resource):
    """
    This class handles requests for a specific block, identified by it's hash.
    """

    def __init__(self, community, block_id):
        resource.Resource.__init__(self)
        self.block_id = urlsafe_b64decode(block_id)
        self.community = community

    def render_GET(self, request):
        """
        .. http:get:: /block/(string: block_id)

        A GET request to this endpoint returns information about a specific block on the blockchain.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/block/AIfwclpXbMimLcf15EG4W5QbbFR9ifUkxCr49aWYtT4=

            **Example response**:

            .. sourcecode:: javascript

                {
                    "block": {
                        "creator": "TGliTmFDTFBLOrhXMbHGgk_Pq0TXYqMOCY7FTbtvwe3sXm9XbbzO0bkPsYfofTeAUUDtcBiPCEP2ntMQLdF-oeVr5FeXPoEbwpE=",
                        "contracts": [],
                        "merkle_root_hash": "pXaGVQhfwppLvJf1aeiDIbIjuNUZKDgAVetusHpwRLw=",
                        "creator_signature": "hDOKk_4lRsFh2eDr5-JL_j30rwUbWSq1DkvkxIxyS4jXNUd2somAY8gyByu6j7YcOp3XIoedXqvNCzUvA1c2Dw==",
                        "time": 1493046869,
                        "id": "ADxyGf6VmgZduESTrQCHDxEJjLX0WPmg9gXjq18j8nc=",
                        "previous_hash": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
                        "target_difficulty": "00ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
                    }
                }
        """
        block = self.community.data_manager.get_block(self.block_id)
        if not block:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "block not found"})

        block_dict = block.to_dict(api_response=True)
        block_index = self.community.data_manager.get_block_index(block.id)
        block_dict["height"] = block_index.height
        return json.dumps({"block": block_dict})
