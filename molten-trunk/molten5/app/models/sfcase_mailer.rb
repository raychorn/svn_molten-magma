class SfcaseMailer < ActionMailer::Base
  def confirmation(support_case)
    setup
    @subject    = "[#{AppConstants::APP_NAME}] Support Case Confirmation"
    @body["support_case"] = support_case
    @recipients = support_case.contact.email
  end
  
  
  private
  
  def setup
    @from       = AppConstants::DEFAULT_FROM_ADDRESS
    @sent_on    = Time.now
    @headers    = {}
  end
end
