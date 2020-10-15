class Sfuser < ActiveRecord::Base
  sync :with => User
  set_primary_key "sf_id"
  belongs_to :sfcontact, :foreign_key => "user_contact_id__c"
  has_many :contacts, :class_name => "Sfcontact", :foreign_key => "owner_id", :order => "portal_last_login_date__c DESC"
  
  #------------------
  # INSTANCE METHODS
  #------------------
  
  # combines the user's first and last name
  def name
    "#{last_name}, #{first_name}".strip
  end
  alias to_s name
  
  def sort_name
    last_name
  end
end
