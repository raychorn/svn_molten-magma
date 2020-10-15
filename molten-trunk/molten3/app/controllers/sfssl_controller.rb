class SfsslController < ApplicationController
    
  def insert
    @msg=updateSSL()    
  end
  
  def updater
    @msg=getUpdateSSL()
  end
end
