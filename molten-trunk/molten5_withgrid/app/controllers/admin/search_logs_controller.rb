class Admin::SearchLogsController < AbstractAdminController
  def list
    @solution_search_logs = SolutionSearchLog.paginate(:per_page => 50,
                        :order => 'created_at DESC',:page => params[:page])
    render(:action => 'list')
  end
  alias index list
end
