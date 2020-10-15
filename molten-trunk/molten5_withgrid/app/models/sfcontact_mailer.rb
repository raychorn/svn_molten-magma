class SfcontactMailer < ActionMailer::Base
  include ActionController::UrlWriter
  
  def forgot_password(contact,port,host)
    setup
    @subject    = "[#{AppConstants::APP_NAME}] Retrieve Your Password"
    @body["contact"] = contact
    @body["host"] = host
    @body["port"] = port
    @recipients = contact.email
  end
  
  def lead_reminder(lead)
    setup
    @subject = "[#{AppConstants::APP_NAME}] Lead Status Request"
    @body["lead"] = lead
    @recipients = lead.owner.email
  end
  
  def confirmation(contact)
    setup
    @subject = "[#{AppConstants::APP_NAME}] Please Confirm Your Account"
    @body["contact"] = contact
    @recipients = contact.email
  end
  
  def owner_notification(comment)
    setup
    @subject = "[#{AppConstants::APP_NAME}] New Comment Posted to Case"
    @body["comment"] = comment
    @recipients = comment.support_case.owner.email
  end
  
  def welcome(sfcontact,contact,email)
    setup
    @subject = "[#{AppConstants::APP_NAME}] - Welcome, please set your password"
    @body["sfcontact"] = sfcontact
    @body["contact"] = contact
    @recipients = email
  end
  
  private
  
  def setup
    @from       = AppConstants::DEFAULT_FROM_ADDRESS
    @sent_on    = Time.now
    @headers    = {}
  end
end
