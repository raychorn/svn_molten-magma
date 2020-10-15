class SfsolutionController < ApplicationController
 
  
  def insert
    @msg=updateSolution()    
  end
  
  def updater
    @msg=getUpdateSolution()
  end
end
