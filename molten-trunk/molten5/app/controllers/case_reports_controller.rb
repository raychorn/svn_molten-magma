# = Case Reports
# 
# The interface for Case Reports may be a bit confusing, so here are some
# clarifications:
# 
# * Case Reports just save the query params, such as <tt>sort</tt>
# * When viewing a report that isn't saved yet, you can click +Save Report As+
#   which will ask you to overwrite an existing report, or name a new report.
# * When viewing a saved report, you can click +Save Report+ to either update
#   its +shared+ status or overwrite a different report.
# 
# What may be confusing is if you view a report and then change the filters et
# al and then want to update that same report. You would then click
# +Save Report As+ and select the report you want to overwrite.
# 
# This is necessary because you're no longer at a saved report so it doesn't
# know which report you want to update.
class CaseReportsController < ApplicationController
  
  ###############
  ### Filters ###
  ###############
  before_filter :set_report, :only => %w(show update destroy)
  before_filter :edit_check, :only => %w(update destroy)
  
  # This is the primary interface for updating or creating reports
  def save_report
    if request.post?
      if @case_report = CaseReport.find(params[:case_report][:id]) rescue false
        update
      else
        create
      end
      redirect_to report_link(@case_report)
    end
  end
  alias_method :save_report_as, :save_report
  
  def create
    @case_report = CaseReport.new({
      :contact_id => current_contact.id,
      :account_id => current_contact.account.id,
      :query => params[:query],
      :shared => (params[:share] == "1"),
      :status_array => cases_status_array,
      :account_ids_array => account_ids_array,
      :column_array => cases_column_array
    }.merge(params[:case_report]))
    flash[:notice] = "Case Report created." if @case_report.save
  end
  
  def update
    @case_report.query = CaseReport.to_options(params[:query])
    %w(sort order).each do |key|
      @case_report.query[key] = params[key.to_sym] if params[key.to_sym]
    end
    @case_report.status_array = cases_status_array
    @case_report.account_ids_array = account_ids_array
    @case_report.column_array = cases_column_array
    @case_report.shared = (params[:share] == "1")
    flash[:notice] = "Case Report updated successfully." if @case_report.save
  end
  
  def destroy
    @case_report.destroy
    render :update do |page|
      page.hide "report_#{@case_report.id}"
    end
  end
  
  private
  
  def edit_check
    if @case_report.editable?(current_contact)
      true
    else
      if request.xhr?
        render :update do |page|
          page.alert "You don't have permission to do this."
        end
      else
        redirect_to(:controller => 'home', :warning => "You don't have permission to do this.")
      end
      false
    end
  end
  
  def set_report
    @case_report = CaseReport.find(params[:id])
  end
  
  def cases_status_array
    params[:case_report_status_array]
  end
  
  def account_ids_array
    params[:case_report_account_array]
  end
  
  def cases_column_array
    params[:case_report_column_array]
  end
  
  def report_link(report)
    raise ArgumentError unless report.is_a?(CaseReport)
    {:controller => 'cases', :action => 'report', :id => report.id}
  end
  
end
