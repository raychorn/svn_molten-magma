class AddFormSubmissionAndTechnicalAdminSetting < ActiveRecord::Migration
  def self.up
    AppSetting.create(:name => "Salesforce Form Submissions", :value => AppSetting::SALESFORCE_FORM_SUBMISSIONS[:no_submit])
    AppSetting.create(:name => "Technical Support Email", :value => "derek.haynes@highgroove.com")
  end

  def self.down
    ["Salesforce Form Submissions","Technical Support Email"].each { |name| AppSetting.find_by_name(name).destroy }
  end
end