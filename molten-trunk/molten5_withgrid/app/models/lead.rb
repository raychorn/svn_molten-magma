class Lead < ActiveRecord::Base
  #################
  ### Behaviors ###
  #################
  establish_connection :salesforce
  set_primary_key "id"
  set_table_name 'lead'
  
  ###################
  ### Assocations ###
  ###################
  belongs_to :owner, :class_name => "User", :foreign_key => "owner_id"
  # combines the user's first and last name
  
  #################
  ### Constants ###
  #################
  
  MOLTEN_REQUEST_RECORD_TYPE = '0123000000000gd'
  
  FREE_EMAIL_DOMAINS = %w(gmail.com hotmail.com yahoo.com)
  
  ###################
  ### Validations ###
  ###################
  validates_presence_of :salutation, :first_name, :last_name, :company, :email,
                        :phone, :country, :title, :street, :city, :state, :postal_code,
                        :business_unit__c, :description,
                        :if => Proc.new { |c| c.validate_attributes == true }
  validate_on_create :validates_email_uniqueness
  validate_on_create :validates_email_not_free
  
  ##########################
  ### Virtual Attributes ###
  ##########################
  
  ########################
  ### Instance Methods ###
  ########################
  
  def validate_attributes=(new_attribute)
    @validate_attributes = new_attribute
  end
  
  def validate_attributes
    @validate_attributes
  end
  
  def name
    "#{first_name} #{last_name}".strip
  end
  
  private
  
  # Email account can't be from a free provider
  def validates_email_not_free
    return if !validate_attributes or email.blank?
    FREE_EMAIL_DOMAINS.each do |domain|
      if email =~ /#{domain}/
        errors.add('email',"must not be a free account.")
      end
    end
  end
  
  # Can't have a contact account and must not have an exisiting
  # lead with the MOLTEN_REQUEST_RECORD_TYPE record type.
  def validates_email_uniqueness
    if validate_attributes == true
      if email and (Contact.find_by_email(email) or Lead.find(:first, :conditions => ["email = ? and record_type_id = ?",email,MOLTEN_REQUEST_RECORD_TYPE]))
        errors.add('email', "A contact already exists with this email address.")
      end
    end
  end
end
