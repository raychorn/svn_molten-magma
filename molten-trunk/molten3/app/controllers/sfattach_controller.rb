class SfattachController < ApplicationController
    
   def insert
    @msg=updateAttachment()    
  end
  
  def updater
    @msg=getUpdateAttachment()
  end
  
end
