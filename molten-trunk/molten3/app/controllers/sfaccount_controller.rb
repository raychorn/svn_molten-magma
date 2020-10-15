require 'rubygems'
class SfaccountController < ApplicationController
    
  def insert
    @msg=updateAccount()    
  end
  
  def updater
    @msg=getUpdateAccount()
  end
  
end
