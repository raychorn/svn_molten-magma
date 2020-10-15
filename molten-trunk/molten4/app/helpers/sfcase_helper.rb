module SfcaseHelper

    def getcontactid(caseid)	
        
	    @case_details=Case.find(:first, :conditions => "id = '#{caseid}'")	
	    @cont_id=@case_details.contact_id	 
	    #@case_details.contact_id 
	    @ssf_id=SelfServiceUser.find(:first, :conditions => "contact_id = '#{@cont_id }'") 
	    @usr_id=User.find(:first, :conditions => "user_contact_id__c  = '#{@cont_id }'") 
	    @def_id="00530000000cBrzAAE"  	 	    
	    
	    render(:layout => false)	
	end
	
	
end
