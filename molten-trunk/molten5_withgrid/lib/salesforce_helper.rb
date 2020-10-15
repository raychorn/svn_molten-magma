module SalesforceHelper
  # Creates a form tag for submitting data to Salesforce via
  # WebToLead. The action taken when the form is submitted is specified by 
  # AppSetting.config("Salesforce Form Submissions").
  #
  # Requires an object hash (ie - {orgid => '122334443'}) and a servlet_name (ie - WebToLead).
  #
  # Options:
  #   :notice => "Flash message to display after form is submitted."
  #     Default: "The form was submitted successfully."
  #   :return_url => Url to send the user to after the form has been submitted.
  #     Default: home_url
  def form_salesforce_tag(object_hash, servlet_name, options = {})
    options = {:notice => "The form was submitted successfully." , :return_url => home_url}.merge(options)
    form_tag = "<form action=\"https://www.salesforce.com/servlet/servlet.#{servlet_name}?encoding=UTF-8\" method=\"POST\">"
    object_field = hidden_field_tag(object_hash.keys.first.to_s,object_hash.values.first.to_s)
    return_field = hidden_field_tag('retURL', "#{options[:return_url]}?notice=#{options[:notice]}")
    hidden_fields = ""
  
    case AppSetting.config("Salesforce Form Submissions")
      when AppSetting::SALESFORCE_FORM_SUBMISSIONS[:no_submit]
        form_tag = form_tag(options[:return_url])
      when AppSetting::SALESFORCE_FORM_SUBMISSIONS[:debug]
        hidden_fields << hidden_field_tag("debug",1)
        hidden_fields << hidden_field_tag("debugEmail",AppSetting.config("Technical Support Email"))
    end
    html =<<-END
      #{form_tag}
        #{object_field}
        #{hidden_fields}
        #{return_field}
    END
  end
  
  # creates a link to the given Salesforce record. 
  def link_to_salesforce(name,record)
    link_to name, "https://na6.salesforce.com/#{record.id}"
  end
end