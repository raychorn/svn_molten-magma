# This model is used to store application settings.
# Settings have the following attributes:
#   name (required) => The name of the setting. Can be human friendly (ie - "Salesforce Form Submissions")
#   - value (required) => The value of the setting. Must be a string.
#   - field_type (required) => The type of form field to use when setting this option. Can either be:
#                                 - text_field (default) => free-form text extry
#                                 - select => Select box.
#                                   If a select box, possible values must be made available in a constant name
#                                   like "Salesforce Form Submissions" => SALESFORCE_FORM_SUBMISSIONS 

class AppSetting < ActiveRecord::Base
  set_primary_key "id"
  #------------------
  # CONSTANTS
  #------------------
  
  # mappings for text-value fields
  SALESFORCE_FORM_SUBMISSIONS = {:no_submit => "Don't Submit to Salesforce",
                                 :debug => "Submit to Salesforce in Debug Mode",
                                 :submit => "Submit to Salesforce" }.freeze
                                 
  SEND_COMMENT_NOTIFICATIONS = {:send_notification => "Yes",
                                :do_not_send_notification => "No"}
  
  
  #------------------
  # VALIDATIONS
  #------------------
  validates_presence_of :name, :value, :field_type
  validates_uniqueness_of :name
  
  #------------------
  # CLASS METHODS
  #------------------
  
  # Returns the value of the config setting with name +name+.
  def self.config(name)
    if setting = find_by_name(name)
      return setting.value
    else
      raise "Could not find config setting with name: #{name}"
    end
  end
  
  # If +field_type+ == 'select', This returns an array of possible value options.
  def possible_values
    AppSetting.const_get(to_constant).values
  end
  
  private
  
  # Converts the setting name to a constant name like:
  #   "Salesforce Form Submissions" => SALESFORCE_FORM_SUBMISSIONS 
  # This is used to retrieve the constant that contains possible setting values when the
  # +field_type+ = select.
  def to_constant
    name.upcase.gsub(' ','_')
  end
end
