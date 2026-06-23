"""启动入口。

DATA_ROOT 来源(优先级 高→低):--data-root > 真实环境变量 > backend/.env。
切 instance 平时改 backend/.env 里的 DATA_ROOT 即可;临时换一套用 --data-root。

  python api.py                          # 用 backend/.env(或真实 env)
  python api.py --data-root D:/Note/n2   # 临时覆盖,不动 .env
  python api.py --port 8003              # 临时换端口(便于并行多开)
"""
import argparse
import os


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-root", default=None,
                    help="临时覆盖 DATA_ROOT(优先于 .env 和真实 env)")
    ap.add_argument("--port", type=int, default=None,
                    help="临时覆盖监听端口(默认走 .env/config 的 PORT=8002)")
    args = ap.parse_args()

    # 关键顺序:--data-root 必须在 import app 之前写进 os.environ,
    # 因为 app.config 在 import 时即读 DATA_ROOT(且 load_dotenv override=False
    # 不会覆盖已 set 的真实 env),这样 CLI flag 才能赢过 .env。
    if args.data_root:
        os.environ["DATA_ROOT"] = os.path.abspath(args.data_root)

    import uvicorn
    from app import app
    from app.config import config

    uvicorn.run(app, host=config.HOST, port=args.port or config.PORT)


if __name__ == "__main__":
    main()
