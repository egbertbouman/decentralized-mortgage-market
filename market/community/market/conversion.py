from market.community.market import conversion_pb2
from market.community.blockchain.conversion import BlockchainConversion


class MarketConversion(BlockchainConversion):

    def __init__(self, community):
        super(MarketConversion, self).__init__(community)

        msg_types = {u'user': (chr(100), conversion_pb2.UserMessage),
                     u'offer': (chr(101), conversion_pb2.OfferMessage),
                     u'accept': (chr(102), conversion_pb2.AcceptMessage),
                     u'reject': (chr(103), conversion_pb2.RejectMessage),
                     u'campaign-update': (chr(104), conversion_pb2.CampaignUpdateMessage)}

        for name, (byte, proto) in msg_types.iteritems():
            self.define_meta_message(byte,
                                     community.get_meta_message(name),
                                     lambda msg, proto=proto: self._encode_protobuf(proto, msg),
                                     lambda placeholder, offset, data, proto=proto:
                                            self._decode_protobuf(proto, placeholder, offset, data))
