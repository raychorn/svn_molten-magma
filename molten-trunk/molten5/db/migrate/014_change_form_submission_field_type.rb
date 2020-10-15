class ChangeFormSubmissionFieldType < ActiveRecord::Migration
  def self.up
    # AppSetting.find_by_name("Salesforce Form Submissions").update_attribute('field_type','select')
  end

  def self.down
  end
end
