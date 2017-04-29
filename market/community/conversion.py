import market_pb2 as pb

from market.dispersy.conversion import BinaryConversion
from protobuf_to_dict import dict_to_protobuf, protobuf_to_dict


class MarketConversion(BinaryConversion):

    def __init__(self, community):
        super(MarketConversion, self).__init__(community, "\x02")

        msg_types = {u'user-request': (chr(1), pb.UserRequestMessage),
                     u'user-response': (chr(2), pb.UserResponseMessage),
                     u'loan-request': (chr(3), pb.LoanRequestMessage),
                     u'loan-reject': (chr(4), pb.LoanRejectMessage),
                     u'offer': (chr(5), pb.OfferMessage),
                     u'accept': (chr(6), pb.AcceptMessage),
                     u'reject': (chr(7), pb.RejectMessage),
                     u'campaign-update': (chr(8), pb.CampaignUpdateMessage),
                     u'signature-request': (chr(9), pb.SignatureRequestMessage),
                     u'signature-response': (chr(10), pb.SignatureResponseMessage),
                     u'contract': (chr(11), pb.ContractMessage),
                     u'block-request': (chr(12), pb.BlockRequestMessage),
                     u'block': (chr(13), pb.BlockMessage)}

        for name, (byte, proto) in msg_types.iteritems():
            self.define_meta_message(byte,
                                     community.get_meta_message(name),
                                     lambda msg, proto=proto: self._encode_protobuf(proto, msg),
                                     lambda placeholder, offset, data, proto=proto:
                                            self._decode_protobuf(proto, placeholder, offset, data))

    def _encode_protobuf(self, message_cls, message):
        return dict_to_protobuf(message_cls, message.payload.dictionary).SerializeToString(),

    def _decode_protobuf(self, message_cls, placeholder, offset, data):
        msg = message_cls()
        msg.ParseFromString(data[offset:])
        return len(data), placeholder.meta.payload.implement(protobuf_to_dict(msg))
