class Admin::SettingsController < AbstractAdminController
  
  before_filter :set_setting, :only => [:edit,:update]
  
  def list
    @settings = AppSetting.find(:all)
    render(:action => 'list')
  end
  alias index list

  def update
    if @setting.update_attributes(params[:setting])
      flash[:notice] = "Setting updated"
      return redirect_to(:action => 'list')
    else
      return render(:action => 'edit')
    end
  end
  
  private
  
  def set_setting
    @setting = AppSetting.find(params[:id])
  end
end
