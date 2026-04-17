// Utilitaire pour déduire le service de validation à partir du rôle
export function getServiceFromRoles(roles) {
  if (!roles || !roles.length) return null;
  if (roles.includes('agent_scolarite')) return 'scolarite';
  if (roles.includes('agent_comptable')) return 'comptabilite';
  if (roles.includes('service_medical')) return 'medical';
  if (roles.includes('bibliotheque')) return 'bibliotheque';
  return null;
}
