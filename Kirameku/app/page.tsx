import HomeClient from "./HomeClient";

// 静态导出模式：数据获取移至 HomeClient (useEffect + fetch)
// 与项目中其他 99% 的页面保持一致
export default function Home() {
  return <HomeClient />;
}
