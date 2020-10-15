class ErrorMailer < ActionMailer::Base
  def search_error(term,exception)
    setup
    @subject    = "[#{AppConstants::APP_NAME}] Search Error"
    @body["term"] = term
    @body["exception"] = exception
    @recipients = ExceptionNotifier.exception_recipients
  end
  
  def index_error(record,exception)
    setup
    @subject    = "[#{AppConstants::APP_NAME}] Index Error"
    @body["record"] = record
    @body["exception"] = exception
    @recipients = ExceptionNotifier.exception_recipients
  end
  
  private
  
  def setup
    @from       = AppConstants::DEFAULT_FROM_ADDRESS
    @sent_on    = Time.now
    @headers    = {}
  end
end
