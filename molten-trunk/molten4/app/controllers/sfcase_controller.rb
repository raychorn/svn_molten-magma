class SfcaseController < ApplicationController
    
  def insert
    @msg=insert_case    
  end
  
  def updater
    @msg=sync_case
  end
  
  def list
    @caselist=Sfcase.find_all
  end
  
  def detail
    @attr=@params["id"]
    @caseinfo = Sfcase.find(:first, :conditions => "sf_id = '#{@attr}'")
    #@caseinfo=Sfcase.find(@params['id'])
    @cid=@caseinfo.sf_id
	@ccommnets=Sfccomment.find(:all, :conditions => "parent_id = '#{@cid}'")
  end
  
  def newcomment
	 @caseid=@params["id"]	 
   	 @case_comment = CaseComment.new
   	 @ccomment=Sfccomment.new
  end

  def createcomment
    #ActiveRecord.establish_connection(:adapter => 'activesalesforce', :sid => sid, :url => api_server_url)
    
    @case_comment = CaseComment.new(params[:case_comment])	    
    if @case_comment.save
      tempHash = Hash.new()  
      @sfccid=@case_comment.id 
      #@sfrec=CaseComment.find(:first, :condition => "id ='#{@sfccid}'")  
      #sqlcc=Sfccomment.new(@sfrec)
      #sqlcc.save
      @ccomment = Sfccomment.new(params[:case_comment])
      @ccomment.save	
      @ccid=@ccomment.id
      sqlUpdate=Sfccomment.find(@ccid)
            
      @currentTime=Time.now
      @currentTime=@currentTime+(7*60 * 60)
      #@frmdate=@currentTime.strftime("%Y-%m-%d%H:%M:%S")  
      tempHash["created_date"]=@currentTime
      tempHash["system_modstamp"]=@currentTime
      tempHash["sf_id"]=@sfccid  
      sqlUpdate.update_attributes(tempHash)           
      
      @parent_id=@case_comment.parent_id
      redirect_to :action => 'detail', :id => @parent_id
    else
      render :action => 'newcomt'	      
    end
  end

end
