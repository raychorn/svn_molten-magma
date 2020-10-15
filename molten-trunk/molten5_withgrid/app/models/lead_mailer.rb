class LeadMailer < ActionMailer::Base
  def notification(lead)
    setup
    @subject = "Thank you for your MOLTEN account request"
    @body["lead"] = lead
    @recipients = lead.email
  end

  private

  def setup
    @from       = AppConstants::DEFAULT_FROM_ADDRESS
    @sent_on    = Time.now
    @headers    = {}
  end
end