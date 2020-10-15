class Admin::DatabaseController < AbstractAdminController

  def size_comparison
    render(:action => 'size_comparison')
  end
  alias index size_comparison
end
