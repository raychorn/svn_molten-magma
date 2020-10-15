class CaseViewSetting < ActiveRecord::Base
  set_primary_key "id"
  #------------------
  # ASSOCIATIONS
  #------------------
  belongs_to :settings, :class_name => "SfcontactSetting", :foreign_key => "sfcontact_setting_id"
  
  #------------------
  # VALIDATIONS
  #------------------
  validates_presence_of :settings
  validates_uniqueness_of :status, :scope => "sfcontact_setting_id"
end
