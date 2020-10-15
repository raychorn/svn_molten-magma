require 'base64'

class AttachmentsController < ProtectedController
  def download
    @attachment = Attachment.find(params[:id])
    send_data Base64.decode64(@attachment.body), :filename => @attachment.name, :type => @attachment.content_type || 'text'
  end
  
  def create
    if [StringIO, String].include?(params[:attachment][:body].class) or params[:attachment][:body].size.zero?
      return redirect_to(:controller => "#{params[:from]}", 
                         :action => 'show', 
                         :id => params[:attachment][:parent_id], 
                         :notice => "Please provide a file to upload.") 
    end
    @attachment = Attachment.new(construct_attachment_params)
    @attachment.validate_attributes = true
    
    if @attachment = @attachment.save_and_clone
      flash[:notice] = "Your attachment was submitted successfully."      
      return redirect_to(:controller => "#{params[:from]}", :action => 'show', :id => params[:attachment][:parent_id],
                         :notice => "Your attachment was submitted successfully.")
    else
      return render(:template => "#{params[:from]}/show", :id => params[:attachment][:parent_id])
    end
  end
  
  def construct_attachment_params
    params[:attachment].merge({
     :body => Base64.encode64(params[:attachment][:body].read),
     :body_length => params[:attachment][:body].size,
     :name => params[:attachment][:body].original_filename
    })
  end
  
  private
  
  # Grabs only those attributes specified in +AppConstants::ATTACHMENT_FIELD_MAPPING+ and converts them into a params string.
  def salesforce_params
    params = {}
    
    # in debug mode?
    if AppSetting.config("Salesforce Form Submissions") == AppSetting::SALESFORCE_FORM_SUBMISSIONS[:debug]
        logger.info("Adding attachment debug params")
        params.merge!({:debug => 1})
        params.merge!({:debugEmail => AppSetting.config("Technical Support Email")})
    end
    
    AppConstants::ATTACHMENT_FIELD_MAPPING.each do |key,value|
      params.merge!({value => @attachment.attributes[key.to_s]})
    end
    logger.info("Created Attachment Params: #{params.to_a.map { |key_value| "#{key_value.first}: #{key_value.last}\n" }}")
    return params
  end
  
  # Submits the attachment to Salesforce.
  def submit_attachment_to_salesforce
    # don't submit if in 'no submit' mode
    return if AppSetting.config("Salesforce Form Submissions") == AppSetting::SALESFORCE_FORM_SUBMISSIONS[:no_submit]
    response = Net::HTTP.post_form(URI.parse('http://www.salesforce.com/servlet/servlet.WebToAttachment'),
                                  salesforce_params)
    logger.info("Response from Salesforce after submitting attachment: #{response}")
  end
end
