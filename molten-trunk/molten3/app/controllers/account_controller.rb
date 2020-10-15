class AccountController < ApplicationController
  
  def list
	@acct=Account.columns
	@sfaccts=Account.find_all
  end
  
  def desc
    @desc=Account.connection.get_entity_def("Account")
    @nm=@desc.columns
    @nm.each do |val|
      @api=val.api_name
    end
    return @nm
  end
  
  def myaccounts
    testId="00130000001FGOUAA4"
    @modAccounts=Account.find(:all, :conditions => "id = '#{testId}' and last_modified_date > '2003-12-18'  ") 
    @cnt=0 
    cdate=nil
    @modAccounts.each do |cn| 
      cdate=cn.last_modified_date 
      @cnt=@cnt+1    
    end
    
       
  end
  
end
