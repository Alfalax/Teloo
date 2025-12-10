# CI/CD Quick Start Guide

## For Developers

### Before Pushing Code

```bash
# Test locally first
./scripts/test-ci-locally.sh

# If all checks pass, push your code
git push origin your-branch
```

### Creating a Pull Request

1. Push your feature branch
2. Create PR to `develop`
3. CI will automatically run
4. Wait for all checks to pass
5. Request review

### Merging to Develop

When PR is merged to `develop`:
- CI runs automatically
- If successful, deploys to staging
- Check Slack for deployment notification

## For DevOps

### Deploying to Staging

**Automatic**: Push to `develop` branch

**Manual**:
1. Go to Actions → "CD - Deploy to Staging"
2. Click "Run workflow"
3. Select `develop` branch
4. Click "Run workflow"

### Deploying to Production

**Prerequisites**:
1. Create version tag: `git tag v1.0.0 && git push origin v1.0.0`
2. Verify CI passed for the tag

**Steps**:
1. Go to Actions → "CD - Deploy to Production"
2. Click "Run workflow"
3. Enter version (e.g., `v1.0.0`)
4. Select deployment type:
   - `kubernetes` - For scalable production
   - `docker-swarm` - For simpler setup
5. Click "Run workflow"
6. Monitor deployment in Actions tab
7. Verify deployment succeeded

### Rolling Back

**Kubernetes**:
```bash
kubectl rollout undo deployment/core-api -n teloo-production
```

**Docker Swarm**:
```bash
docker service rollback teloo_core-api
```

**Complete Rollback**:
Re-deploy previous version tag through GitHub Actions

## Common Commands

### Check Deployment Status

**Kubernetes**:
```bash
kubectl get pods -n teloo-production
kubectl logs -f deployment/core-api -n teloo-production
```

**Docker Swarm**:
```bash
docker stack services teloo
docker service logs -f teloo_core-api
```

### Test Health

```bash
# Staging
curl https://staging.teloo.com/health

# Production
curl https://teloo.com/health
curl https://api.teloo.com/v1/health
```

## Troubleshooting

### CI Failing

1. Check workflow logs in Actions tab
2. Run `./scripts/test-ci-locally.sh` to reproduce
3. Fix issues and push again

### Deployment Failing

1. Check deployment logs in Actions
2. Check service logs (kubectl/docker)
3. Verify secrets are configured
4. Check resource availability

### Need Help?

- Check `DEPLOYMENT_GUIDE.md` for detailed instructions
- Check `.github/workflows/README.md` for workflow details
- Contact DevOps team on Slack: #teloo-devops
- Emergency: oncall@teloo.com

## Important Links

- **Staging**: https://staging.teloo.com
- **Production**: https://teloo.com
- **API Docs**: https://api.teloo.com/docs
- **GitHub Actions**: https://github.com/your-org/teloo-v3/actions
- **Grafana**: https://grafana.teloo.com
- **Slack**: #teloo-deployments

## Best Practices

✅ **DO**:
- Test locally before pushing
- Deploy to staging first
- Monitor deployments for 30 minutes
- Document any issues
- Communicate with team

❌ **DON'T**:
- Deploy to production on Fridays
- Skip staging testing
- Deploy without monitoring
- Ignore failing tests
- Deploy during peak hours
