# Fields present in BUILD object at SFDC
# Subversion properties
#
# $LastChangedDate: 2006-06-05 09:52:45 -0700 (Mon, 05 Jun 2006) $
# $Author: misha $
# $Revision: 41 $
# $HeadURL: http://capps.moltenmagma.com/svn/sfsrc/trunk/builds/sfdc_objects.py $
# $Id: sfdc_objects.py 41 2006-06-05 16:52:45Z misha $
build_objects = (
                  'Access_Path__c', \
                  'Account__c', \
                  'Build_Date__c', \
                  'Build_ID__c', \
                  'Build_Path__c', \
                  'Build_Type__c', \
                  'Common__c', \
                  'CreatedById', \
                  'CreatedDate', \
                  'Date_Accepted__c', \
                  'Date_Approved__c', \
                  'Date_Sent__c', \
                  'File_Uploaded_to_Intraware__c', \
                  'ftp_Account__c', \
                  'ftp_Password__c', \
                  'ftp_Server__c', \
                  'Id', \
                  'Intraware_Sync__c', \
                  'Intraware_Sync_Error_Details__c', \
                  'LastModifiedById', \
                  'LastModifiedDate', \
                  'Linux_32__c', \
                  'Linux_64__c', \
                  'Magma_Intraware_Upload__c', \
                  'Magma_Intraware_Upload_Error_Details__c', \
                  'Master_Campaign__c', \
                  'MD5_Digest__c', \
                  'Name', \
                  'Needs_Check__c', \
                  'OwnerId', \
                  'Payload_Size__c', \
                  'Platform_List__c', \
                  'Purpose__c', \
                  'Recipient__c', \
                  'SHA1_Digest__c', \
                  'Status__c', \
                  'Sun_64__c', \
                  'SystemModstamp', \
                  'Version__c' \
                  )
# Initialize the string to be comma delimited representation of build objects
build_object_list = ""
# populate the string
for bo in build_objects[:len(build_objects)-1]:
    build_object_list = build_object_list + bo + ', '
    
build_object_list = build_object_list + build_objects[len(build_objects)-1]
#print build_object_list
# SFDC table name that holds BUILDS
build_table = "Build__c"
# Business rule: criteria we use to filer build records we care about
build_criteria = " where \
                    Build_Type__c = 'Patch Build' \
                  and \
                    Build_Path__c != '' \
                  and \
                    (\
                    Magma_Intraware_Upload__c = '' \
                    or \
                    Magma_Intraware_Upload__c = 'In Process' \
                    or \
                    Magma_Intraware_Upload__c = 'Error'\
                    )"
#
# build SOQL statement to be used in a query
get_build_objects_soql="Select " \
    + build_object_list \
    + " from " \
    + build_table \
    + build_criteria
# end