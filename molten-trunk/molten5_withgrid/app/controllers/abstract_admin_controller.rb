class AbstractAdminController < ApplicationController
  authorize :condition_method => :is_super_user?
  
  private
  
  # only super users and higher can gain access by default to the admin area.
  def authorized?
    if !current_contact.privilege?(AppConstants::PRIVILEGE[:super_user])
      flash[:warning]  = "You are not authorized to access this area"
      false
    else
      true
    end 
  end
end
