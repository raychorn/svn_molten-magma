class SfattachController < ApplicationController
    
   def insert
    @msg=insert_attachment    
  end
  
  def updater
    @msg=sync_attachment
  end
  
end
