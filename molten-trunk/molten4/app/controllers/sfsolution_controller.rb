class SfsolutionController < ApplicationController
 
  
  def insert
    @msg=insert_solution    
  end
  
  def updater
    @msg=sync_solution
  end
end
