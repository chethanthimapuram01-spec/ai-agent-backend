# Production Deployment Guide

## Quick Deploy

### Render (Recommended)
1. Push to GitHub: `git push origin main`
2. Go to [render.com](https://render.com)
3. New Web Service → Connect GitHub repo
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add env vars: `OPENAI_API_KEY=your-key`, `ENVIRONMENT=production`

### Railway
```bash
npm install -g @railway/cli
railway login && railway init && railway up
railway variables set OPENAI_API_KEY=your-key ENVIRONMENT=production
```

### AWS Elastic Beanstalk
```bash
pip install awsebcli
eb init -p python-3.11 ai-agent-backend
eb create production
eb setenv OPENAI_API_KEY=your-key ENVIRONMENT=production
eb deploy
```

## Environment Variables

**Required:**
- `OPENAI_API_KEY` - Your OpenAI API key
- `ENVIRONMENT=production`

**Optional (with defaults):**
- `HOST=0.0.0.0`
- `PORT=8000`
- `WORKERS=4`
- `LOG_LEVEL=info`

See `.env.example` for complete list.

## Verification

```bash
# Before deploy
python verify_deployment.py
pytest test_endpoints.py test_agent_workflow.py -v

# After deploy
curl https://your-url.com/health
curl https://your-url.com/docs
```

## Deployment Files

- `Procfile` - Render/Railway startup command
- `Dockerfile` - Container deployment
- `render.yaml` - Render configuration
- `railway.json` - Railway configuration
- `requirements.txt` - Python dependencies
- `.env.example` - Environment template
- `verify_deployment.py` - Pre-deployment checks

## Support

- [Render Docs](https://render.com/docs)
- [Railway Docs](https://docs.railway.app)
- [AWS EB Docs](https://docs.aws.amazon.com/elasticbeanstalk/)

---

**Ready to deploy?** Run `python verify_deployment.py` to check!
