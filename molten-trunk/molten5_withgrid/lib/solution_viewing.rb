module  SolutionViewing
  # Used to create the conditional for viewing a solution. 
  def set_solution_viewable_status_for_contact(contact)
    conditions = Sfsolution.contact_viewing_restrictions(contact)
    conditions.first << " AND (is_published = 'True' or is_published = '1')"
    return conditions
  end
end