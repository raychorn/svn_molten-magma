class SfcaseController < ApplicationController
    
  def insert
    @msg=updateCase()    
  end
  
  def updater
    @msg=getUpdateCase()
  end
  
end
