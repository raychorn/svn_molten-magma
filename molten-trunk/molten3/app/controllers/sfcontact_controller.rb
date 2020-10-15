class SfcontactController < ApplicationController
    
  def insert
    @msg=updateContact()    
  end
  
  def updater
    @msg=getUpdateContact()
  end
  
end
