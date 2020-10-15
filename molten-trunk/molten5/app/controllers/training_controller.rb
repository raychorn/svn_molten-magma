class TrainingController < ProtectedController
 
  def index
    render(:action => 'index')
  end

  def blasttalusmigration
    render(:action => 'BlastTalusMigration')
  end

  def reportsqueries
    render(:action => 'ReportsQueries')
  end

  def snapenwrap
    render(:action => 'SnapEnwrap')
  end

  def strengthhypercellsonLine
    render(:action => 'Strength_HyperCells_OnLine')
  end

  def hydrawebinar
    render(:action => 'HydraWebinar')
  end
  #private
  
end
