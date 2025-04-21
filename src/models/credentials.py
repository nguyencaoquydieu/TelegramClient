class CredentialSet:
    def __init__(self, api_id, api_hash, phone):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
    
    def to_dict(self):
        return {
            'api_id': self.api_id,
            'api_hash': self.api_hash,
            'phone': self.phone
        }
    
    @staticmethod
    def from_dict(data):
        return CredentialSet(
            data['api_id'],
            data['api_hash'],
            data['phone']
        )