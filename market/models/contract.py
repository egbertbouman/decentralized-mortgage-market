import hashlib

from base64 import urlsafe_b64encode
from storm.properties import Int, RawStr

from market.database.types import Enum
from market.dispersy.crypto import LibNaCLPK
from market.models import ObjectType
from market.models.mortgage import Mortgage
from market.models.investment import Investment
from market.util.misc import verify_libnaclpk


class Contract(object):
    """
    This class represents an contract between 2 users.
    """

    __storm_table__ = 'contract'
    _id = RawStr(name='id', primary=True)
    previous_hash = RawStr()
    from_id = RawStr()
    from_signature = RawStr()
    to_id = RawStr()
    to_signature = RawStr()
    document = RawStr()
    type = Enum(ObjectType)
    time = Int()

    def __init__(self):
        self.previous_hash = ''
        self.from_id = ''
        self.from_signature = ''
        self.to_id = ''
        self.to_signature = ''
        self.document = ''
        self.time = 0

    def __storm_pre_flush__(self):
        assert not self._id or self._id == self.id, 'Contract.id has changed'
        self._id = self.id

    def __str__(self):
        return '%s %s %d %s %s' % (self.from_id, self.to_id, self.time, self.previous_hash, self.document)

    @property
    def id(self):
        return hashlib.sha256(str(self)).digest()

    def sign(self, member):
        assert isinstance(member._ec, LibNaCLPK), 'Only supporting libnacl crypto for now'
        assert member.public_key in (self.from_id, self.to_id)

        if member.public_key == self.from_id:
            self.from_signature = member.sign(str(self))
        elif member.public_key == self.to_id:
            self.to_signature = member.sign(str(self))

    def verify(self, member=None):
        assert member is None or member.public_key in (self.from_id, self.to_id)

        data = str(self)
        if member is None:
            return verify_libnaclpk(self.from_id, data, self.from_signature) and \
                   verify_libnaclpk(self.to_id, data, self.to_signature)

        if member.public_key == self.from_id:
            return member.verify(data, self.from_signature)
        elif member.public_key == self.to_id:
            return member.verify(data, self.to_signature)

    def get_object(self):
        if self.type == ObjectType.MORTGAGE:
            return Mortgage.from_bin(self.document)
        elif self.type == ObjectType.INVESTMENT:
            return Investment.from_bin(self.document)

    def to_dict(self, api_response=False):
        contract_dict = {
            'previous_hash': urlsafe_b64encode(self.previous_hash) if api_response else self.previous_hash,
            'from_id': urlsafe_b64encode(self.from_id) if api_response else self.from_id,
            'from_signature': urlsafe_b64encode(self.from_signature) if api_response else self.from_signature,
            'to_id': urlsafe_b64encode(self.to_id) if api_response else self.to_id,
            'to_signature': urlsafe_b64encode(self.to_signature) if api_response else self.to_signature,
            'document': urlsafe_b64encode(self.document) if api_response else self.document,
            'type': self.type.name if api_response else self.type.value,
            'time': self.time
        }

        if api_response:
            contract_dict['id'] = urlsafe_b64encode(self.id)

        return contract_dict

    @staticmethod
    def from_dict(contract_dict):
        try:
            contract_type = ObjectType(contract_dict['type'])
        except ValueError:
            return None

        contract = Contract()
        contract.previous_hash = contract_dict['previous_hash']
        contract.from_id = contract_dict['from_id']
        contract.from_signature = contract_dict['from_signature']
        contract.to_id = contract_dict['to_id']
        contract.to_signature = contract_dict['to_signature']
        contract.document = contract_dict['document']
        contract.type = contract_type
        contract.time = contract_dict['time']
        return contract