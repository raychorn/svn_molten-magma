class UserController < ApplicationController
  def list
	@usr=User.columns
	@usrec=User.find_all	
  end
end
