module  AppConstants
  # Update this before deploying...should be the tag
  MOLTEN_VERSION = "3.0.116.2"
 
#  APP_NAME = "MOLTEN – Magma Design Automation, Inc."
  APP_NAME = "MOLTEN"
  
  APP_URL = "http://molten.moltenmagma.com"
  
  SHUTDOWN_DATES = [Date.strptime('02/06/2009',fmt='%m/%d/%Y'),Date.strptime('02/08/2009',fmt='%m/%d/%Y')]
  #SHUTDOWN_NOTICE = "Dear Customer,<br><br>Magma Design Automation Inc is observing a company-wide shutdown from 11/24/2008 to 12/01/2008. MOLTEN USA support during this time will be at minimal. Please expect delays in responses.<br><br>Additionally, Molten will be observing a regularly scheduled downtime each day from 7a to 8a PT (U.S. Pacific Time)<br><br>Thank you for your co-operation and understanding.<br><br>Sincerely,<br>MOLTEN TEAM USA"
  #SHUTDOWN_NOTICE = "Dear Customer,<br><br>Magma Design Automation Inc is observing a company-wide shutdown from 12/19/2008 to 01/04/2008. MOLTEN USA support during this time will be minimal. Please expect delays in responses.<br><br>During this time, Molten will continue to observe a regularly scheduled downtime each day from 7a to 8a PT (U.S. Pacific Time)<br><br>Thank you for your cooperation and understanding.<br><br>Sincerely,<br>MOLTEN TEAM USA"
  SHUTDOWN_NOTICE = "Dear Customer,<br/>MOLTEN will be shut down from 8:30 p.m. (PT) Feb. 6 to 2:00 a.m. Feb. 7 for maintenance.<br/><br/>After that, we will resume daily maintenance shut-downs between 7:00 a.m. and 8:00 a.m. (PT).<br/><br/>We apologize for the inconvenience."
  #
  #SHUTDOWN_NOTICE = "Dear Customer,<br><br>Recently you may have received an email from Molten that welcomed you to Molten or in reference to your user password needing to be changed.  In case you encounter any difficulties with accessing Molten we welcome you to use the the Molten self-help feature, found below by clicking the \"Forgot Your Password?\" link, to resolve your Molten Access issues.<br><br>Sincerely,<br>MOLTEN TEAM"
  #SHUTDOWN_NOTICE = "Dear Customer,<br><br>Molten is offline for maintenance until further notice. Please expect delays in responses.<br><br>Thank you for your co-operation and understanding.<br><br>Sincerely,<br>MOLTEN TEAM USA"
  ALT_SHUTDOWN_NOTICE = "Dear Customer,<br><br>Molten will continue to observe a regularly scheduled downtime each day from 7a to 8a PT (U.S. Pacific Time)<br><br>Thank you for your cooperation and understanding.<br><br>Sincerely,<br>MOLTEN TEAM USA"

  ALLOW_LOGINS = true

  SUPPORT_EMAIL = "molten-support@molten-magma.com"
  
  SEARCH_INFO = "&nbsp;<small>(<i>Please enter an \"*\" after your keyword to widen your search when applicable.</i>)</small>"

  # Used to authenticate when refreshing cached content
  CACHE_KEY = "00N30000000cAL7"
  
  # Number of support cases to show on home page
  RECENTLY_UPDATED_LIMIT = 5

  # Number of popular solutions to show on home page and left side
  MOST_POPULAR_LIMIT = 5

  # Number of days to go back when determining popular solutions
  MOST_POPULAR_LAST_N_DAYS = 30
  
  # Maximum characters in the case subject length when showing in a list
  CASE_SUBJECT_LENGTH = 70
  
  # Maximum characters in the solution name lenght when showing in a list
  SOLUTION_NAME_LIMIT = 47
  
  # Maximum solutions to show per/section on the home page
  SOLUTION_HOME_LIMIT = 5
  
  # Default relevancy for solutions
  DEFAULT_SOLUTION_RELEVANCY = 50
  
  # Limit the number of cases when viewing cases
  CASE_COUNT_LIMIT_ALL = 15
  CASE_COUNT_LIMIT_SPECIFIC = 30
  
  # Maximum length (in characters) of the length of solution notes to display
  # in search solution results.
  SOLUTION_SEARCH_NOTE_LIMIT = 450
  
  # Number of Solutions to display per category and search result page
  SOLUTIONS_PER_PAGE = 20

  # Count new solutions in last N days
  NEW_SOLUTIONS_LAST_N_DAYS = 30
  
  # The order to sort cases on the Support Cases View
  CASE_SORT_ORDER = ["New","Open","In Process","CR Pending",
    "Enhancement CR Pending","Awaiting Cust. Response",
    "Awaiting R&D Input","On Hold","Solving","Team Hold",
    "Pending Complete Test Case","Not Started",
    "Closed","Closed Duplicate","Closed Fixed by Subsequent Change","Closed User Error","Closed Will Not Fix"]
    
  # Maximum # of Recent cases and solutions to show in the sidebar
  RECENT_LIMIT = 5
  
  # Default from address for automated emails.
  DEFAULT_FROM_ADDRESS = "noreply@molten-magma.com"
  
  # Friendly names for solution ratings...worst to best rating.
  FRIENDLY_RATING_NAMES = ["No Way", "A Little Helpful", "OK", "Very Helpful"]
  
  # Emails are sent to contacts if they haven't confirmed their account in this length of time.
  CONFIRMATION_RANGE = 6.months.ago
  
  # Contacts have this long to respond to the confirmation request.
  CONFIRMATION_RANGE_LIMIT = 8.month.ago
  
  # Limit the number of articles in the sidebar
  ARTICLE_LIMIT = 5
  
  # Length of the article body to display on the articles list page
  ARTICLE_LIST_BODY_LENGTH = 400
  ARTICLE_LIST_TITLE_LENGTH = 80
  
  # Limit the total number of cases to display in the RSS Feed to this number.
  CASE_FEED_LIMIT = 10
  
  # This character string surrounds the comment creator user id in the comment body.
  COMMENT_CREATOR_DELIMATOR = "Posted By"
  
  # Case to Web2Case parameter mapping.
  CASE_FIELD_MAPPING = {
    # required
    :subject => 'subject',
    :sf_type => 'type',
    :customer_priority__c => '00N30000000c9mJ',
    :description => 'description',
    :operating_system__c => '00N30000000c9mK',
    :product__c => '00N30000000hu0j',
    :component__c => '00N30000000c9mM',
    :query_build_view__c => '00N30000000c9mO',
    # optional
    :dataor_test_case_provided__c => '00N30000000cAL7',
    :customer_tracking__c => '00N30000000c9mN',
    :time_stamp_build__c => '00N30000000boEH',
    :version_number__c => '00N30000000boNL',
    :foundry__c => '00N30000000cFH7',
    :hdl__c => '00N30000000cFH7',
    :design_geometryn_m__c => '00N30000000cFH3',
    :std_cell_library__c => '00N30000000cHRr',
    :speed_m_hz__c => '00N30000000cFHD',
    :cell_count_k_objects__c => '00N30000000cFH9',
    # hidden
    :record_type_id => 'record_type_id',
    # API 7 :is_visible_in_css => 'is_visible_in_css',
    :is_visible_in_self_service => 'is_visible_in_self_service', # API 8 and up
    :origin => 'origin',
    #:contact_id => 'contact_id',
    :workaround_available__c => 'N/A',
    :status => 'status'
      }
      
  # Attachment to Web2Attachment parameter mapping
  ATTACHMENT_FIELD_MAPPING = {
    :body => 'body',
    :body_length => 'body_length',
    :is_private => 'is_private',
    :name => 'name',
    :parent_id => 'parent_id'
  }
      
  # Limit on the number of queries to find when updating records in SalesforceSync. 
  QUERY_LIMIT = 300
  
  # The key used to encode the file download token.
  FILE_DOWNLOAD_KEY  = "Sync_Key_Dac_Magma_Dac_Support_$"
  
  # The digest used with OpenSSL for encoding the file download token.
  FILE_DOWNLOAD_DIGEST    = 'md5'
  
  # The length of time cookies should remain
  COOKIE_TIME_LIMIT = 24.hours.from_now
  
  # The domain for the LAVA cookie
  LAVA_COOKIE_DOMAIN = '.lava.com'
  
  # The available portal privilege levels.
  PRIVILEGE = {
    :admin => 'Admin',
    :marketing_admin => 'Marketing Admin',
    :support_admin => 'Support Admin',
    :user_manager => 'User Manager',
    :super_user => 'Super User',
    :member => 'Member',
    :account_requester => 'Account Requester',
    :partners => 'Partners',
    :inactive => 'Inactive',
  }
  
  # These users can login
  PRIVILEGES_WITH_ACCESS = AppConstants::PRIVILEGE.values.reject { |p| p == AppConstants::PRIVILEGE[:inactive] or p == AppConstants::PRIVILEGE[:account_requester] }
  
  CLASS_MAPPINGS = {
   'Account' => 'Sfaccount', 
   'User' => 'Sfuser', 
   'SelfServiceUser' => 'Sfssl', 
   'Case' => 'Sfcase',
   'Contact' => 'Sfcontact',
   'Solution' => 'Sfsolution',
   'Attachment' => 'Sfattach',
   'CaseComment' => 'Sfccomment',
   'MoltenPost' => 'SfmoltenPost',
   'CategoryNode' => 'Sfcatnode',
   'CategoryData' => 'Sfcatdata',
   'Case_Watcher' => 'SfcaseWatcher',
   'Case_Watcher_List' => 'SfcaseWatcherList',
   'Group' => 'Sfgroup',
   'Component' => 'Sfcomponent',
   'Product_Team' => 'SfproductTeam'
                  }
  
  # Columns that should be ignored when syncing. 
  SYNC_COLUMNS_TO_IGNORE = { Attachment => ['body']}
  
  # Any support case custom field names entered here will be ignored
  # when indexing.
  # Example: [:comments_text]
  IGNORE_FIELDS = [:comments_text, :attachment_names]

  ######################
  ### Forum Settings ###
  ######################
  
  MAX_ABUSE_COUNT = 10
end