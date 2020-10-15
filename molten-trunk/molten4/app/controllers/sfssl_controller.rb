class SfsslController < ApplicationController
    
  def insert
    @msg=insert_ssl    
  end
  
  def updater
    @msg=sync_ssl
  end
end
