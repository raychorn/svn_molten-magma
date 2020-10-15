class ErrorController < ApplicationController
  def updater
    @msg=updateError()
  end
end
