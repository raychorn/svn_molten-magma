class SfuserController < ApplicationController
  
  def insert
    @msg=updateUser()    
  end
  
  def updater
    @msg=getUpdateUser()
  end
end
