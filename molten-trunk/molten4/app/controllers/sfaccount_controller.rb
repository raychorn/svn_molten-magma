require 'rubygems'
class SfaccountController < ApplicationController
    
  def insert
    @msg=insert_account
  end
  
  def updater
    @msg=sync_account
  end
  
end
