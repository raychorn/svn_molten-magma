class SfuserController < ApplicationController
  
  def insert
    @msg=insert_user
  end
  
  def updater
    @msg=sync_user
  end
end
