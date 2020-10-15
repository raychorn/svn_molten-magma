require 'salesforce_config'

class SalesforceController < ProtectedController
  def get_config
    cfg = SalesforceConfig.new
    render(:action => 'get_config.rjs')
  end
  
end
