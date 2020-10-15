import pprint

from sfCrudObject import SFCrudObject, DetailRecordMixin


class SFTechCampaign(SFCrudObject):
    obj = "Tech_Campaign__c"

class SFTechCampaignComment(SFCrudObject, DetailRecordMixin):
    obj = "Tech_Campaign_Comment__c"
