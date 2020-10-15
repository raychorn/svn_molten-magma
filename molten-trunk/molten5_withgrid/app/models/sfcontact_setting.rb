class SfcontactSetting < ActiveRecord::Base
  set_primary_key "id"
  #------------------
  # ASSOCIATIONS
  #------------------
  belongs_to :sfcontact
  has_many :case_view_settings
  has_one :case_columns_setting
  
  #------------------
  # VALIDATIONS
  #------------------
  validates_presence_of :sfcontact
  validates_uniqueness_of :sfcontact_id
  
  
  #################
  ### Callbacks ###
  #################
  after_create :initialize_case_columns_setting
  
  #------------------
  # METHODS
  #------------------
  
  # Returns the +CaseViewSetting+ for this contact and +status+. 
  # If the record doesn't exist yet, it is created.
  def case_view(status)
    case_view_settings.find_by_status(status) || case_view_settings.create(:status => status)
  end
  
  private
  
  # create local settings unless it already exists.
  def initialize_case_columns_setting
    create_case_columns_setting unless CaseColumnsSetting.find_by_sfcontact_setting_id("#{id}")
  end
end
