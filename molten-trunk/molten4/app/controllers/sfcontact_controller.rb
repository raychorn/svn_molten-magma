class SfcontactController < ApplicationController
    
  def insert
    @msg=insert_contact    
  end
  
  def updater
    @msg=sync_contact
  end
  
end
